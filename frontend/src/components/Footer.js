import React from 'react';
import { Github, Linkedin, MessageSquare, Facebook, MapPin, Mail, Phone } from 'lucide-react';

const Footer = () => {
    return (
        <footer className="footer bg-white border-t border-border pt-16 pb-10 px-4 relative z-10">
            <div className="container mx-auto max-w-7xl">
                <div className="grid md:grid-cols-2 gap-12 mb-12">
                    <div>
                        <h5 className="text-[0.95rem] font-bold mb-5 text-text-primary">Team Members</h5>
                        <div className="developer-card">
                            <p className="font-bold text-text-primary mb-0.5">K Mounika,M kamalini,L Kavyanjali</p>
                            <p className="text-text-secondary text-[0.82rem] mb-4">AI/ML Dept</p>
                        </div>
                    </div>
                    <div>
                        <h5 className="text-[0.95rem] font-bold mb-5 text-text-primary">Contact</h5>
                        <ul className="list-none space-y-3.5">
                            <li className="flex items-center gap-3 text-text-secondary text-[0.88rem]">
                                <MapPin size={16} className="text-accent shrink-0" />Hyderabad
                            </li>
                            <li className="flex items-center gap-3 text-text-secondary text-[0.88rem]">
                                <Mail size={16} className="text-accent shrink-0" /> booksageAI@gmail.com
                            </li>
                            <li className="flex items-center gap-3 text-text-secondary text-[0.88rem]">
                                <Phone size={16} className="text-accent shrink-0" /> +880 1834 363 533
                            </li>
                        </ul>
                    </div>
                </div>
                <div className="text-center pt-6 border-t border-border text-text-muted text-[0.82rem]">
                    <p>&copy; 2025 BookSage-AI. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
